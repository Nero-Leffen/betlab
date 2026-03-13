# Claude AI Integration Setup

This document explains how to connect this repository to Claude AI via the
[`anthropics/claude-code-action`](https://github.com/anthropics/claude-code-action)
GitHub Actions workflow.

---

## Prerequisites

- You must be a **repository admin** to add secrets and install GitHub Apps.
- An **Anthropic account** with an API key (create one at
  [console.anthropic.com](https://console.anthropic.com)).

---

## Step 1 — Install the Claude GitHub App

Install the official Claude GitHub App to this repository:

👉 **<https://github.com/apps/claude>**

The app grants Claude the permissions it needs to read and write issues, pull
requests, and code on your behalf.

---

## Step 2 — Add the `ANTHROPIC_API_KEY` secret

1. Go to **Settings → Secrets and variables → Actions** in this repository.
2. Click **New repository secret**.
3. Fill in the fields:
   - **Name:** `ANTHROPIC_API_KEY`
   - **Value:** Your Anthropic API key (starts with `sk-ant-…`)
4. Click **Add secret**.

> ⚠️ **Never commit your API key directly to any file in the repository.**
> Always reference it via `${{ secrets.ANTHROPIC_API_KEY }}`.

---

## Step 3 — (Optional) Generate a GitHub PAT for elevated access

If you need Claude to perform actions that require a Personal Access Token
(PAT) — for example pushing commits to protected branches — create a fine-
grained PAT and add it as a second secret:

1. Go to **GitHub → Settings → Developer settings → Personal access tokens →
   Fine-grained tokens → Generate new token**.
2. Under **Repository access** select *Only select repositories* and choose
   this repo.
3. Grant the following **Repository permissions**:
   - **Contents:** Read and write
   - **Issues:** Read and write
   - **Pull requests:** Read and write
4. Click **Generate token** and copy the value.
5. Add it as a repository secret named `GH_PAT` (Settings → Secrets →
   Actions → New repository secret).
6. Update `.github/workflows/claude.yml` to pass the token:

   ```yaml
   - name: Run Claude Code
     uses: anthropics/claude-code-action@v1
     with:
       anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
       github_token: ${{ secrets.GH_PAT }}
   ```

---

## How to use Claude

Once the workflow is active, mention **`@claude`** in:

| Location | How to trigger |
|----------|---------------|
| Issue body or title | Include `@claude` when opening the issue |
| Issue comment | Post a comment containing `@claude` |
| Pull request review | Submit a review containing `@claude` |
| PR review comment | Post an inline comment containing `@claude` |

Claude will respond directly in the same thread.

---

## Workflow file reference

The workflow is located at `.github/workflows/claude.yml`.  It listens for
the triggers above and runs `anthropics/claude-code-action@v1` using the
`ANTHROPIC_API_KEY` secret.

For advanced configuration options (custom model, allowed tools, system
prompt, etc.) see the
[official documentation](https://github.com/anthropics/claude-code-action).
