# Automated GitHub Publishing Instructions (For Grok Bot / CLI Agent)

Unpack this archive on your workstation or Grok Bot workspace and run the steps below to publish the repository to GitHub.

---

## Copy-Paste Prompt for Grok Bot

> Unzip the `gemini-airgapped-drive-relay` archive, enter the `gemini-airgapped-drive-relay` directory, run `python3 reference-cli/drive_pull_verify.py --self-test` to verify all integrity checks pass, and execute `./publish_to_github.sh` to create a public GitHub repository named `gemini-airgapped-drive-relay` and push the `main` branch. Return the live GitHub URL when finished.

---

## Direct Shell Execution

Ensure `git` and the GitHub CLI (`gh`) are installed and authenticated (`gh auth status`), then run:

```bash
unzip gemini-airgapped-drive-relay-v2.zip
cd gemini-airgapped-drive-relay
chmod +x publish_to_github.sh
./publish_to_github.sh
```

To customize the repository name:

```bash
REPO_NAME="google-airgapped-agent-relay" ./publish_to_github.sh
```
