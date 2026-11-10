"""Count distinct incomplete endpoint nodes without inventing upstream repairs."""
import hashlib
import os
from pathlib import Path

import duckdb
import pyarrow.parquet as pq
from kg_microbe_curation.identity import CurationError

from .census import _metadata
from .content_inventory import _checked_file, _space, _write_json
from .storage.parquet import file_hash, fsync_directory, safe_path


def triage(manifest_path: Path, pin: str, output: Path, *, all_partitions=False):
    manifest_path, output = safe_path(manifest_path), safe_path(output, exists=False)
    data, manifest = _metadata(manifest_path)
    if hashlib.sha256(data).hexdigest() != pin:
        raise CurationError('Inventory pin mismatch')
    selected = manifest['partitions'] if all_partitions else manifest['partitions'][:1]
    files = [str(_checked_file(manifest_path.parent, part)) for part in selected]
    _space(output.parent, 2 * 1024**3)
    output.mkdir()
    with duckdb.connect(config={'memory_limit': '512MB', 'threads': '2'}) as db:
        db.read_parquet(files).create_view('inventory')
        db.execute('CREATE TEMP VIEW endpoints AS '
                   "SELECT occurrence_id, primary_knowledge_source, 'subject' AS role, "
                   'subject AS id, subject_label AS label, subject_category AS category, '
                   'subject_present_in_nodes AS present FROM inventory UNION ALL '
                   "SELECT occurrence_id, primary_knowledge_source, 'object', object, "
                   'object_label, object_category, object_present_in_nodes FROM inventory')
        db.execute("CREATE TEMP TABLE gaps AS SELECT *, coalesce(trim(label),'')='' AS missing_label, "
                   "coalesce(trim(category),'')='' AS missing_category FROM endpoints "
                   "WHERE present AND (coalesce(trim(label),'')='' OR coalesce(trim(category),'')='')")
        # A self-loop contributes one occurrence to a node, even when both roles are incomplete.
        nodes = db.sql('SELECT id, missing_label, missing_category, '
                       'count(DISTINCT occurrence_id) AS affected_occurrences, '
                       'list(DISTINCT role ORDER BY role) AS roles, '
                       'list(DISTINCT primary_knowledge_source ORDER BY primary_knowledge_source) AS sources '
                       'FROM gaps GROUP BY id, missing_label, missing_category ORDER BY id').to_arrow_table()
        destination = output / 'nodes.parquet'
        pq.write_table(nodes, destination, compression='zstd')
        with destination.open('rb') as handle:
            os.fsync(handle.fileno())
        if not pq.read_table(destination).equals(nodes):
            raise CurationError('Persisted node artifact differs from computed node table')
        totals = db.execute('SELECT count(DISTINCT occurrence_id), count(DISTINCT id), count(*) '
                            'FROM gaps').fetchall()[0]
        missing = db.execute('SELECT count(DISTINCT occurrence_id) FROM endpoints '
                             'WHERE NOT present').fetchall()[0][0]
        profiles = db.execute("SELECT split_part(id,':',1), missing_label, missing_category, "
                              'count(DISTINCT id), count(DISTINCT occurrence_id) FROM gaps '
                              'GROUP BY 1,2,3 ORDER BY 4 DESC,1').fetchall()
        sources = db.execute('SELECT primary_knowledge_source,count(DISTINCT occurrence_id), '
                             'count(DISTINCT id) FROM gaps GROUP BY 1 ORDER BY 2 DESC,1').fetchall()
        if nodes.num_rows != totals[1]:
            raise CurationError('Conflicting metadata states for the same pinned node')
        if all_partitions and totals[0] != sum(p['incomplete_node_occurrences'] for p in manifest['profile']):
            raise CurationError('Incomplete occurrence totals disagree with preparation')
        rows = db.execute('SELECT count(*) FROM inventory').fetchall()[0][0]
    # Every scan above must refer to the originally pinned bytes. The endpoint
    # view remains lazy, so check again after the final scan, not only at open.
    for part in selected:
        _checked_file(manifest_path.parent, part)
    if file_hash(manifest_path) != pin:
        raise CurationError('Inventory manifest changed during triage')
    result = {'artifact_type': 'edgemech-node-metadata-triage/v1', 'inventory_sha256': pin,
              'nodes_sha256': manifest['nodes_sha256'], 'selected_partitions': len(selected),
              'selected_occurrences': rows, 'complete_inventory': all_partitions,
              'affected_occurrences': totals[0], 'distinct_incomplete_nodes': totals[1],
              'incomplete_endpoint_roles': totals[2], 'missing_node_occurrences': missing,
              'nodes_artifact_sha256': file_hash(output / 'nodes.parquet'),
              'prefix_profiles': [dict(zip(('prefix', 'missing_label', 'missing_category',
                                           'distinct_nodes', 'affected_occurrences'), p, strict=True))
                                  for p in profiles],
              'source_profiles': [dict(zip(('source', 'affected_occurrences', 'distinct_nodes'), p, strict=True))
                                  for p in sources],
              'repair_route': 'KG-Microbe node assembly and owning ontology/source release; no local label fabrication',
              'limitations': ['Prefixes identify namespaces, not proven root causes.',
                              'Per-source/node/role counts overlap; do not sum them as distinct occurrences.',
                              'Metadata incompleteness does not establish scientific falsity.']}
    fsync_directory(output)
    _write_json(output / 'manifest.json', result)
    return result
