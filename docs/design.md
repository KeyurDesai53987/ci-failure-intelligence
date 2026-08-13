# Design and decision record

## Unit of analysis

A workflow run is the release-level outcome. A job is a matrix or workflow component. A step is the narrowest visible metadata unit. The analysis preserves these levels because counting every failed matrix job as an independent failed workflow would inflate the incident rate.

## Outcome semantics

Success and failure are decisive outcomes. Cancelled and skipped runs are reported separately. Failure rate is `failure / (success + failure)` and does not silently treat skipped work as healthy.

## Failure signature

The first step with `conclusion=failure` is a navigation aid. It is not called a root cause. GitHub job metadata can show where execution first became visibly unsuccessful, but causality requires logs, code changes, environment evidence, and often a rerun.

## Acquisition limitation

The GitHub runs endpoint uses page-based retrieval. Because the repository remains active, new runs can enter while pages are fetched. The manifest therefore records the selection exactly, and validation checks uniqueness. A production collector would poll incrementally by run ID/time and store a durable high-water mark.

## Privacy decision

Only metadata already visible in the public Actions interface is stored. Logs were excluded because they can contain noisy environment details and are unnecessary for demonstrating honest run/job/step aggregation.
