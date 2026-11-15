#!/usr/bin/env bash
# Creates progressive commits (one per task) as the assignment requires.
# 1) Create an EMPTY repo on GitHub named CSA08-<RegisterNumber>-Assignment5
# 2) In this folder run:  bash git_commits.sh https://github.com/<you>/CSA08-<RegisterNumber>-Assignment5.git
# TIP: better still, run the commits on different days / after each task while you work.
set -e
git init -b main
git add README.md requirements.txt .gitignore .vscode run_all.py
git commit -m "Add README, requirements and runner"
git add PartA_Design
git commit -m "Part A: design documents A1-A5"
git add shared
git commit -m "Add shared cleaning, generator and sentiment modules"
git add Task01_B1
git commit -m "B1: cleaning pipeline, SQLite, charts, pandas comparison"
git add Task02_B2
git commit -m "B2: adversarial data, SQL injection, sentiment failures"
git add Task03_B3
git commit -m "B3: loops vs pandas vs SQL benchmark and profile"
git add Task04_B4
git commit -m "B4: sentiment agreement, index timing, production decision"
git add -A
git diff --cached --quiet || git commit -m "Final touches"
[ -n "$1" ] && git remote add origin "$1" && git push -u origin main
