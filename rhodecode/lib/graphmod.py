"""
Modified mercurial DAG graph functions that re-uses VCS structure

It allows to have a shared codebase for DAG generation for hg and git repos
"""

nullrev = -1


def grandparent(parentrev_func, lowestrev, roots, head):
    """
    Return all ancestors of head in roots which revision is
    greater or equal to lowestrev.
    """
    pending = set([head])
    seen = set()
    kept = set()
    llowestrev = max(nullrev, lowestrev)
    while pending:
        r = pending.pop()
        if r >= llowestrev and r not in seen:
            if r in roots:
                kept.add(r)
            else:
                pending.update([p for p in parentrev_func(r)])
            seen.add(r)
    return sorted(kept)


def _dagwalker(repo, revs, alias):
    if not revs:
        return

    if alias == 'hg':
        cl = repo._repo.changelog.parentrevs
        repo = repo
    elif alias == 'git':
        def cl(rev):
            return [x.revision for x in repo[rev].parents()]
        repo = repo

    lowestrev = min(revs)
    gpcache = {}

    knownrevs = set(revs)
    for rev in revs:
        ctx = repo[rev]
        parents = sorted(set([p.revision for p in ctx.parents
                              if p.revision in knownrevs]))
        mpars = [p.revision for p in ctx.parents if
                 p.revision != nullrev and p.revision not in parents]

        for mpar in mpars:
            gp = gpcache.get(mpar)
            if gp is None:
                gp = gpcache[mpar] = grandparent(cl, lowestrev, revs, mpar)
            if not gp:
                parents.append(mpar)
            else:
                parents.extend(g for g in gp if g not in parents)

        yield (ctx.revision, 'C', ctx, parents)


def _colored(dag):
    """annotates a DAG with colored edge information

    For each DAG node this function emits tuples::

      (id, type, data, (col, color), [(col, nextcol, color)])

    with the following new elements:

      - Tuple (col, color) with column and color index for the current node
      - A list of tuples indicating the edges between the current node and its
        parents.
    """
    seen = []
    colors = {}
    newcolor = 1

    getconf = lambda rev: {}

    for (cur, type, data, parents) in dag:

        # Compute seen and next
        if cur not in seen:
            seen.append(cur)  # new head
            colors[cur] = newcolor
            newcolor += 1

        col = seen.index(cur)
        color = colors.pop(cur)
        next = seen[:]

        # Add parents to next
        addparents = [p for p in parents if p not in next]
        next[col:col + 1] = addparents

        # Set colors for the parents
        for i, p in enumerate(addparents):
            if not i:
                colors[p] = color
            else:
                colors[p] = newcolor
                newcolor += 1

        # Add edges to the graph
        edges = []
        for ecol, eid in enumerate(seen):
            if eid in next:
                bconf = getconf(eid)
                edges.append((
                    ecol, next.index(eid), colors[eid],
                    bconf.get('width', -1),
                    bconf.get('color', '')))
            elif eid == cur:
                for p in parents:
                    bconf = getconf(p)
                    edges.append((
                        ecol, next.index(p), color,
                        bconf.get('width', -1),
                        bconf.get('color', '')))

        # Yield and move on
        yield (cur, type, data, (col, color), edges)
        seen = next
