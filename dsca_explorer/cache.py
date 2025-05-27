"""
================================================================================
DSCA Explorer Cache Module - Change Log
================================================================================

BEFORE:
-------
- Used hash-based change detection (via layer_hash).
- detect_new_or_updated_layers returned two lists: new_layers and updated_layers.
- No field-level change tracking or metadata about what changed.
- No timestamps or audit trail for changes.
- No standardized structure for representing changes.
- Cache stored only layer hashes.

AFTER:
------
- Introduced ChangeRecord dataclass to standardize change metadata, including:
    - source, layer_id, change_type, changed_fields, detection_time.
- detect_new_or_updated_layers now returns a list of ChangeRecord objects.
- Implements field-level diffing for granular change detection.
- Each change record includes a timestamp (detection_time).
- Cache now stores the full layer dict, not just a hash.
- Added serialize_changes utility for export compatibility.
- Added defensive logic to field_level_diff to handle legacy or corrupted cache
  entries (e.g., if old cache stored hashes as strings instead of dicts).
- Ready for integration with export and CLI modules.

================================================================================
"""



import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, Tuple, Any, List, Literal
from datetime import datetime

CACHE_FILE = Path("dsca_layer_cache.json")

"""
Changelog - 26MAY25
New caching method.
Adding export function for changelog in export.py

Before
Used only hash-based change detection (layer_hash).
Returned two lists: new_layers, updated_layers.
No field-level change tracking.
No timestamps or metadata about what changed.
No standardized change record structure.

After
Uses a ChangeRecord dataclass to standardize change metadata.
Performs field-level diffing for granular change detection.
Records timestamps for each detected change.
Returns a list of ChangeRecord objects (not just raw dicts).
Cache stores the full layer dict, not just a hash.
Includes a utility to serialize changes for export.
"""

@dataclass
class ChangeRecord:
    source: str
    layer_id: str
    change_type: Literal["NEW", "UPDATED"]
    changed_fields: Dict[str, Tuple[Any, Any]]
    detection_time: datetime

    def to_serializable(self):
        d = asdict(self)
        d["detection_time"] = self.detection_time.isoformat()
        return d

def load_cached_data() -> Dict[str, dict]:
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_cache(cache: Dict[str, dict]):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)

def field_level_diff(old_layer, new_layer):
    # If either is not a dict, treat as a full replacement
    if not isinstance(old_layer, dict) or not isinstance(new_layer, dict):
        return {"__all__": (old_layer, new_layer)}
    changed = {}
    all_keys = set(old_layer.keys()) | set(new_layer.keys())
    for k in all_keys:
        old_val = old_layer.get(k)
        new_val = new_layer.get(k)
        if old_val != new_val:
            changed[k] = (old_val, new_val)
    return changed


def detect_new_or_updated_layers(layers: List[dict]) -> List[ChangeRecord]:
    """
    Detects new or updated layers compared to the cache.
    Returns a list of ChangeRecord objects.
    """
    cached_layers = load_cached_data()
    changes: List[ChangeRecord] = []
    new_cache: Dict[str, dict] = {}

    for l in layers:
        key = f"{l.get('source','')}|{l.get('endpoint','')}|{l.get('name','')}"
        new_cache[key] = l
        cached = cached_layers.get(key)
        if not cached:
            # New layer
            changes.append(ChangeRecord(
                source=l.get('source', ''),
                layer_id=key,
                change_type="NEW",
                changed_fields={k: (None, v) for k, v in l.items()},
                detection_time=datetime.utcnow()
            ))
        else:
            # Compare fields
            diff = field_level_diff(cached, l)
            if diff:
                changes.append(ChangeRecord(
                    source=l.get('source', ''),
                    layer_id=key,
                    change_type="UPDATED",
                    changed_fields=diff,
                    detection_time=datetime.utcnow()
                ))

    save_cache(new_cache)
    return changes

def serialize_changes(changes: List[ChangeRecord]) -> List[dict]:
    return [c.to_serializable() for c in changes]
