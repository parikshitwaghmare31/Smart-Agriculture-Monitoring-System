# GitHub Guide — Smart Agriculture Monitoring System

## 1. Initialize the repository

```bash
cd smart-agriculture
git init
git add .
git status   # sanity check: .env, node_modules/, venv/ should NOT appear (see .gitignore)
```

## 2. First commit

```bash
git commit -m "Initial commit: Smart Agriculture Monitoring System (FastAPI + React + ML + MQTT)"
```

## 3. Create the GitHub repository

Using the GitHub CLI:
```bash
gh repo create smart-agriculture-monitoring --public --source=. --remote=origin
```

Or manually: create an empty repo on github.com (no README/license, since
this project already has them), then:
```bash
git remote add origin https://github.com/<your-username>/smart-agriculture-monitoring.git
```

## 4. Push

```bash
git branch -M main
git push -u origin main
```

## 5. Recommended repo hygiene

- **Branch protection**: require PRs into `main` once you have collaborators.
- **GitHub Actions CI** (optional but resume-strengthening): add a workflow
  that runs `pip install -r backend/requirements.txt && python -m pytest`
  and `npm ci && npm run build` in `frontend/` on every push.
- **Secrets**: if you add CI/CD later, store `MONGO_URI`, MQTT credentials,
  etc. in GitHub Actions Secrets — never in the repo.
- **Releases**: tag stable versions, e.g. `git tag v1.0.0 && git push --tags`.

## 6. Suggested commit workflow going forward

```bash
git checkout -b feature/add-alerting
# ... make changes ...
git add .
git commit -m "Add email alert when soil moisture drops below threshold"
git push -u origin feature/add-alerting
# open a Pull Request on GitHub
```

## 7. What NOT to commit

Already handled by `.gitignore`, but worth knowing why:
- `backend/.env` — contains real credentials/connection strings
- `frontend/node_modules/` — regenerated via `npm install`
- `backend/venv/` — regenerated via `pip install -r requirements.txt`
- `backend/logs/*.log` — runtime output, not source
- Large trained models are fine to commit here since they're small (~KB-MB
  for this project), but for bigger models consider Git LFS.
