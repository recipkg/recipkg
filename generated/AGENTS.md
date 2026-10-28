# Working on the generated Recipkg CLI

- This is the Python 3.11+ reference implementation, using only the standard library at runtime.
- The canonical product input lives in `recipkg/recipkg`, under `recipes/recipkg/`. Preserve its observable behavior and complete recursive material.
- Update canonical template/skill requirements there before refreshing `src/recipkg/data/`. Keep English and Simplified Chinese resources aligned.
- Five primary actions only print prompts. Explicit `search` obtains GitHub discovery metadata; `check` and prompt rendering stay offline. No command executes recipe content or calls a model.
- Preserve user edits, unrelated Git work, and skill ownership boundaries. Never add source, binaries, hooks, or links to recipe archives.
- Run `PYTHONPATH=src python3 -m unittest discover -s tests -v`. Set `RECIPKG_RECIPE_ROOT` to a canonical checkout for the resource integration test; report skipped integration checks honestly.
- Verify a built wheel outside this checkout. Do not commit build output, caches, environments, tokens, or user data. Use local checks rather than waiting for CI.
- GitHub repositories publishing Recipkg recipes must carry the `recipkg` topic; a discovery result is not a validated package.
