#!/bin/sh

pip install -r requirements-dev.txt

git config --local core.hooksPath .githooks/
