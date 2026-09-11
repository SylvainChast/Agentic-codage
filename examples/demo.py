#!/usr/bin/env python3
"""Exercise the real CLI in an isolated Git project, using explicit simulated costs/review."""
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1]
CLI = SOURCE / "bin" / "framework"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="New or empty destination; defaults to a retained temp directory")
    args = parser.parse_args()
    root = args.output.resolve() if args.output else Path(tempfile.mkdtemp(prefix="agentic-demo-"))
    if root.exists() and any(root.iterdir()):
        raise SystemExit("Destination must be empty")
    root.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SOURCE / "examples" / "tiny-project", root, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    (root / ".gitignore").write_text("__pycache__/\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(root)], check=True)

    def cli(*args):
        result = subprocess.run([sys.executable, str(CLI), "--root", str(root), *args],
                                capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError(result.stderr or result.stdout)
        return json.loads(result.stdout)

    cli("init", "--name", "Démonstration · coûts et revue simulés")
    path = root / ".framework" / "policy.json"
    policy = json.loads(path.read_text())
    policy["checks"] = [dict(name="pricing-tests", argv=["{python}", "-m", "unittest", "discover", "-s", "tests", "-v"], timeout_seconds=30)]
    path.write_text(json.dumps(policy, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    criteria = ["Le total de 100 EUR à 20 pour cent vaut 120 EUR", "Les montants négatifs sont refusés"]
    task = cli("task", "create", "--title", "Livrer le calcul TTC (simulation)", "--owner", "demo-writer",
               "--scope", "src", "--scope", "tests", "--resource", "api:pricing",
               "--criterion", criteria[0], "--criterion", criteria[1],
               "--deliverable", "Calcul TTC et tests", "--budget-minor", "2000", "--max-runs", "5")
    tid = task["id"]
    cli("lease", "acquire", tid, "--owner", "demo-writer")
    cli("task", "start", tid, "--actor", "demo-writer")
    for outcome, amount, purpose, actor in (("failed", "75", "implementation", "demo-writer"),
                                            ("succeeded", "125", "implementation", "demo-writer"),
                                            ("succeeded", "50", "review", "demo-reviewer")):
        cli("run", "record", tid, "--actor", actor, "--model", "simulation-no-llm",
            "--purpose", purpose, "--outcome", outcome, "--cost-source", "estimate", "--llm-cost-minor", amount,
            "--cost-note", "Montant fictif de démonstration, aucune facture ni appel LLM",
            "--summary", "Exécution simulée pour illustrer les reprises et leur coût",
            "--next-step", "Exercer le mécanisme de preuve et de revue")
    proof = cli("verify", tid)
    cli("task", "submit", tid, "--actor", "demo-writer")
    review = cli("review", "record", tid, "--reviewer", "demo-reviewer", "--verdict", "approve",
                 "--criterion", criteria[0], "--criterion", criteria[1], "--evidence", proof["id"],
                 "--summary", "Simulation du mécanisme de revue ; pas de vraie revue indépendante")
    cli("task", "accept", tid, "--review", review["id"], "--actor", "demo-maintainer")
    cli("check")
    cli("map")
    cli("map", "--check")
    print(json.dumps(dict(project=str(root), map=str(root / "docs" / "carte-du-code.html"),
                          simulated=True, costs=cli("costs")), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
