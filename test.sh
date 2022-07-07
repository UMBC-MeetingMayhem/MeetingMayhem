#!/bin/bash

rm -rf MeetingMayhem/__tests__/__pycache__/
python3 -m unittest MeetingMayhem/__tests__/*
rm -rf MeetingMayhem/__tests__/__pycache__/
git restore MeetingMayhem/site.db
