# Description: Post-processes graphify-out/graph.html to add advanced filtering:
# file-type checkboxes, degree range slider, field-aware search syntax, filter chips.

import re

HTML_PATH = "graphify-out/graph.html"

INJECTED_CSS = """
/* ---- Enhanced filters (injected) ---- */
#filter-bar {
  padding: 0 12px 10px;
  border-bottom: 1px solid #2a2a4e;
  font-size: 12px;
}
#filter-bar.collapsed .filter-body { display: none; }
#filter-bar.collapsed .filter-toggle::after { content: "\u25b6"; }
.filter-toggle {
  cursor: pointer; color: #aaa; font-size: 11px;
  text-transform: uppercase; letter-spacing: 0.05em;
  padding: 8px 0 4px; user-select: none; display: flex; align-items: center; gap: 6px;
}
.filter-toggle:hover { color: #e0e0e0; }
.filter-toggle::after { content: "\u25bc"; font-size: 9px; color: #666; }
.filter-body { padding-top: 6px; }
.filter-row { display: flex; gap: 16px; flex-wrap: wrap; align-items: flex-start; }
.filter-group { min-width: 120px; }
.filter-group label { display: flex; align-items: center; gap: 5px; cursor: pointer; padding: 2px 0; }
.filter-group label:hover { color: #fff; }
.filter-group input[type="checkbox"] {
  appearance: none; -webkit-appearance: none;
  width: 13px; height: 13px; border: 1.5px solid #3a3a5e; border-radius: 3px;
  background: #0f0f1a; cursor: pointer; position: relative; flex-shrink: 0;
}
.filter-group input[type="checkbox"]:checked {
  background: #4E79A7; border-color: #4E79A7;
}
.filter-group input[type="checkbox"]:checked::after {
  content: ''; position: absolute; left: 3px; top: 0.5px;
  width: 4px; height: 7px; border: solid #fff;
  border-width: 0 2px 2px 0; transform: rotate(45deg);
}
.filter-group .count { color: #555; font-size: 11px; }

.degree-range-wrap { display: flex; align-items: center; gap: 8px; padding: 2px 0; }
.degree-range-wrap input[type="range"] {
  width: 80px; height: 4px; -webkit-appearance: none; appearance: none;
  background: #3a3a5e; border-radius: 2px; outline: none; cursor: pointer;
}
.degree-range-wrap input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none; width: 14px; height: 14px; border-radius: 50%;
  background: #4E79A7; border: none; cursor: pointer;
}
.degree-range-wrap .degree-val {
  color: #aaa; font-size: 12px; min-width: 18px; text-align: center;
}

/* Filter chips */
#filter-chips { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 6px; min-height: 0; }
#filter-chips:empty { display: none; }
.filter-chip {
  display: inline-flex; align-items: center; gap: 3px;
  background: #2a2a4e; border: 1px solid #3a3a5e;
  padding: 2px 6px; border-radius: 4px; font-size: 11px; color: #ccc; cursor: default;
}
.filter-chip .chip-close {
  cursor: pointer; color: #666; font-size: 13px; line-height: 1;
  margin-left: 2px; padding: 0 1px;
}
.filter-chip .chip-close:hover { color: #e0e0e0; }
"""

INJECTED_HTML = """
  <div id="filter-bar">
    <div id="filter-chips"></div>
    <div class="filter-toggle" onclick="toggleFilterBar()">Filters</div>
    <div class="filter-body">
      <div class="filter-row">
        <div class="filter-group" id="type-filter-group"></div>
        <div class="filter-group" id="degree-filter-group">
          <div style="color:#aaa;margin-bottom:4px">Degree</div>
          <div class="degree-range-wrap">
            <input type="range" id="degree-min" min="0" max="39" value="0">
            <span class="degree-val" id="degree-min-val">0</span>
            <span style="color:#555">&ndash;</span>
            <input type="range" id="degree-max" min="0" max="39" value="39">
            <span class="degree-val" id="degree-max-val">39</span>
          </div>
        </div>
      </div>
    </div>
  </div>
"""

INJECTED_JS = """
// === Enhanced filtering (injected) ===
const _fileTypeCounts = {};
RAW_NODES.forEach(function(n) {
  var ft = n.file_type || 'unknown';
  _fileTypeCounts[ft] = (_fileTypeCounts[ft] || 0) + 1;
});

var _degreeMin = 0;
var _degreeMax = 39;
(function() {
  // Compute actual degree range
  var ds = RAW_NODES.map(function(n) { return n.degree; });
  _degreeMax = Math.max.apply(null, ds);
  document.getElementById('degree-min').max = _degreeMax;
  document.getElementById('degree-min').value = 0;
  document.getElementById('degree-max').max = _degreeMax;
  document.getElementById('degree-max').value = _degreeMax;
  document.getElementById('degree-max-val').textContent = _degreeMax;
})();

// Build type filter checkboxes
var typeGroup = document.getElementById('type-filter-group');
var _typeCbs = {};
var typeOrder = ['code', 'document', 'rationale'];
typeOrder.forEach(function(ft) {
  if (!_fileTypeCounts[ft]) return;
  var label = document.createElement('label');
  var cb = document.createElement('input');
  cb.type = 'checkbox'; cb.checked = true;
  cb.setAttribute('data-type', ft);
  cb.addEventListener('change', function() { _applyFilters(); });
  label.appendChild(cb);
  label.appendChild(document.createTextNode(' ' + ft + ' '));
  var countSpan = document.createElement('span');
  countSpan.className = 'count';
  countSpan.textContent = _fileTypeCounts[ft];
  label.appendChild(countSpan);
  typeGroup.appendChild(label);
  _typeCbs[ft] = cb;
});

// Degree slider sync
document.getElementById('degree-min').addEventListener('input', function() {
  var v = parseInt(this.value);
  var max = parseInt(document.getElementById('degree-max').value);
  if (v > max) { v = max; this.value = v; }
  document.getElementById('degree-min-val').textContent = v;
  _applyFilters();
});
document.getElementById('degree-max').addEventListener('input', function() {
  var v = parseInt(this.value);
  var min = parseInt(document.getElementById('degree-min').value);
  if (v < min) { v = min; this.value = v; }
  document.getElementById('degree-max-val').textContent = v;
  _applyFilters();
});

// Combined filter — degree ghosts instead of hides to preserve edge visibility
function _applyFilters() {
  _degreeMin = parseInt(document.getElementById('degree-min').value);
  _degreeMax = parseInt(document.getElementById('degree-max').value);
  var activeTypes = {};
  Object.keys(_typeCbs).forEach(function(ft) { if (_typeCbs[ft].checked) activeTypes[ft] = true; });
  var degreeActive = _degreeMin > 0 || _degreeMax < _degreeMax_global;
  var updates = RAW_NODES.map(function(n) {
    var sf = (n.source_file || '').toLowerCase();
    var hidden = hiddenCommunities.has(n.community) || !activeTypes[n.file_type]
      || (_filePrefix && sf.indexOf(_filePrefix) === -1);
    var outOfDegree = n.degree < _degreeMin || n.degree > _degreeMax;
    if (hidden) {
      return { id: n.id, hidden: true };
    }
    if (degreeActive && outOfDegree) {
      // Ghost: keep "visible" so vis-network preserves edges to this node
      return { id: n.id, hidden: false, opacity: 0.04, size: 2, font: { size: 0 } };
    }
    // Restore original visual
    return { id: n.id, hidden: false, opacity: 1.0, size: n.size, font: n.font };
  });
  nodesDS.update(updates);
  updateSelectAllState();
  _updateFilterChips();
}

// Override legend toggle to use combined filter
(function() {
  var legendCbs = document.querySelectorAll('#legend .legend-cb');
  legendCbs.forEach(function(cb, idx) {
    var cid = LEGEND[idx] ? LEGEND[idx].cid : idx;
    cb.setAttribute('data-cid', cid);
    var clone = cb.cloneNode(true);
    cb.parentNode.replaceChild(clone, cb);
    clone.addEventListener('change', function() {
      var c = parseInt(clone.getAttribute('data-cid'));
      if (c >= 0) {
        if (clone.checked) hiddenCommunities.delete(c);
        else hiddenCommunities.add(c);
        clone.closest('.legend-item').classList.toggle('dimmed', !clone.checked);
      }
      _applyFilters();
    });
  });
})();

// Override select-all
document.getElementById('select-all-cb').addEventListener('change', function() {
  var hide = !this.checked;
  LEGEND.forEach(function(c) {
    if (hide) hiddenCommunities.add(c.cid); else hiddenCommunities.delete(c.cid);
  });
  document.querySelectorAll('#legend .legend-item').forEach(function(item) {
    item.classList.toggle('dimmed', hide);
  });
  document.querySelectorAll('#legend .legend-cb').forEach(function(cb) {
    cb.checked = !hide;
  });
  _applyFilters();
});

// Filter chips
function _updateFilterChips() {
  var chipsEl = document.getElementById('filter-chips');
  chipsEl.innerHTML = '';
  // Type chips
  Object.keys(_typeCbs).forEach(function(ft) {
    if (!_typeCbs[ft].checked) {
      var chip = document.createElement('span');
      chip.className = 'filter-chip';
      chip.innerHTML = '<span>type:' + ft + '</span><span class="chip-close" data-action="type:' + ft + '">&times;</span>';
      chipsEl.appendChild(chip);
    }
  });
  if (_degreeMin > 0 || _degreeMax < _degreeMax_global) {
    var chip = document.createElement('span');
    chip.className = 'filter-chip';
    chip.innerHTML = '<span>degree:' + _degreeMin + '-' + _degreeMax + '</span><span class="chip-close" data-action="degree-reset">&times;</span>';
    chipsEl.appendChild(chip);
  }
  if (_filePrefix) {
    var chip = document.createElement('span');
    chip.className = 'filter-chip';
    chip.innerHTML = '<span>file:' + _filePrefix + '</span><span class="chip-close" data-action="file-reset">&times;</span>';
    chipsEl.appendChild(chip);
  }
  // Chip close handlers
  chipsEl.querySelectorAll('.chip-close').forEach(function(el) {
    el.addEventListener('click', function(e) {
      e.stopPropagation();
      var action = el.getAttribute('data-action');
      if (action.startsWith('type:')) {
        var ft = action.slice(5);
        if (_typeCbs[ft]) { _typeCbs[ft].checked = true; }
        _applyFilters();
      } else if (action === 'degree-reset') {
        document.getElementById('degree-min').value = 0;
        document.getElementById('degree-max').value = _degreeMax_global;
        document.getElementById('degree-min-val').textContent = 0;
        document.getElementById('degree-max-val').textContent = _degreeMax_global;
        _applyFilters();
      } else if (action === 'file-reset') {
        _filePrefix = '';
        _applyFilters();
      }
    });
  });
}

var _degreeMax_global = _degreeMax;
var _filePrefix = '';

// Replace search input to nuke original event listeners
(function() {
  var oldInput = document.getElementById('search');
  var newInput = oldInput.cloneNode(true);
  oldInput.parentNode.replaceChild(newInput, oldInput);
  var results = document.getElementById('search-results');

  newInput.addEventListener('input', function() {
    var q = newInput.value.toLowerCase().trim();
    results.innerHTML = '';
    var hasField = /\\b(type|community|degree|file):/i.test(q);
    if (!hasField) {
      if (!q) { results.style.display = 'none'; return; }
      var matches = RAW_NODES.filter(function(n) { return n.label.toLowerCase().indexOf(q) !== -1; }).slice(0, 20);
      if (!matches.length) { results.style.display = 'none'; return; }
      results.style.display = 'block';
      matches.forEach(function(n) {
        var el = document.createElement('div');
        el.className = 'search-item';
        el.textContent = n.label;
        el.style.borderLeft = '3px solid ' + n.color.background;
        el.style.paddingLeft = '8px';
        el.onclick = function() {
          network.focus(n.id, { scale: 1.5, animation: true });
          network.selectNodes([n.id]);
          showInfo(n.id);
          results.style.display = 'none';
          newInput.value = '';
        };
        results.appendChild(el);
      });
      return;
    }
    // Field:value syntax
    results.style.display = 'none';
    var labelQ = q;
    var typeMatch = q.match(/\\btype:([\\w,-]+)/);
    var communityMatch = q.match(/\\bcommunity:(\\d+)/);
    var degreeMatch = q.match(/\\bdegree:([\\d>-]+)/);
    var fileMatch = q.match(/\\bfile:(\\S+)/);

    if (typeMatch) {
      var types = typeMatch[1].split(',');
      Object.keys(_typeCbs).forEach(function(ft) {
        _typeCbs[ft].checked = types.indexOf(ft) !== -1;
      });
      labelQ = labelQ.replace(typeMatch[0], '').trim();
    }
    if (communityMatch) {
      var cid = parseInt(communityMatch[1]);
      document.querySelectorAll('#legend .legend-cb').forEach(function(cb) {
        var itemCid = parseInt(cb.getAttribute('data-cid'));
        if (itemCid === cid) {
          cb.checked = true;
          hiddenCommunities.delete(cid);
          cb.closest('.legend-item').classList.remove('dimmed');
        } else if (itemCid >= 0) {
          cb.checked = false;
          hiddenCommunities.add(itemCid);
          cb.closest('.legend-item').classList.add('dimmed');
        }
      });
      labelQ = labelQ.replace(communityMatch[0], '').trim();
    }
    if (degreeMatch) {
      var dv = degreeMatch[1];
      if (dv.indexOf('-') !== -1) {
        var parts = dv.split('-');
        document.getElementById('degree-min').value = parseInt(parts[0]) || 0;
        document.getElementById('degree-max').value = parseInt(parts[1]) || _degreeMax_global;
      } else if (dv.indexOf('>') !== -1) {
        document.getElementById('degree-min').value = parseInt(dv.slice(1)) || 0;
        document.getElementById('degree-max').value = _degreeMax_global;
      } else {
        var v = parseInt(dv);
        document.getElementById('degree-min').value = v;
        document.getElementById('degree-max').value = v;
      }
      document.getElementById('degree-min-val').textContent = document.getElementById('degree-min').value;
      document.getElementById('degree-max-val').textContent = document.getElementById('degree-max').value;
      labelQ = labelQ.replace(degreeMatch[0], '').trim();
    }
    if (fileMatch) {
      _filePrefix = fileMatch[1].toLowerCase();
      labelQ = labelQ.replace(fileMatch[0], '').trim();
    }
    _applyFilters();
    if (labelQ) {
      var matches = RAW_NODES.filter(function(n) { return n.label.toLowerCase().indexOf(labelQ) !== -1; }).slice(0, 20);
      if (matches.length) {
        results.style.display = 'block';
        results.innerHTML = '';
        matches.forEach(function(n) {
          var el = document.createElement('div');
          el.className = 'search-item';
          el.textContent = n.label;
          el.style.borderLeft = '3px solid ' + n.color.background;
          el.style.paddingLeft = '8px';
          el.onclick = function() {
            network.focus(n.id, { scale: 1.5, animation: true });
            network.selectNodes([n.id]);
            showInfo(n.id);
            results.style.display = 'none';
            newInput.value = '';
          };
          results.appendChild(el);
        });
      }
    }
  });
})();

// Toggle filter bar collapse
function toggleFilterBar() {
  document.getElementById('filter-bar').classList.toggle('collapsed');
}
"""

def inject_after(html: str, marker: str, code: str) -> str:
    idx = html.find(marker)
    if idx == -1:
        raise ValueError(f"Marker not found: {marker[:60]}")
    return html[:idx + len(marker)] + code + html[idx + len(marker):]


def inject_before(html: str, marker: str, code: str) -> str:
    idx = html.find(marker)
    if idx == -1:
        raise ValueError(f"Marker not found: {marker[:60]}")
    return html[:idx] + code + html[idx:]


def main():
    with open(HTML_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    # 1. Inject CSS before </style> (inside the style tag)
    html = inject_before(html, "</style>", INJECTED_CSS)

    # 2. Inject filter bar HTML between search-wrap and info-panel
    html = inject_before(html, '<div id="info-panel">', INJECTED_HTML)

    # 3. Inject JS before </body>
    html = inject_before(html, "</body>", "<script>\n" + INJECTED_JS + "\n</script>\n")

    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    print("Enhanced graph.html with advanced filtering UI")


if __name__ == "__main__":
    main()
