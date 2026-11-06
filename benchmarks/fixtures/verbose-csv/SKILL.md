---
name: verbose-csv
description: This skill helps you to extract CSV records when preparing tabular reports.
---

# CSV records

## Background

Tabular data has a rich and fascinating history that stretches across decades of computing. Early business applications relied on simple text representations, and those representations gradually became a shared language across many different industries. The humble comma separated file became a familiar part of office life, academic research, and personal computing. Its historical significance reflects a broader story about accessible information and collaboration between communities.

The story of this particular project began with an enthusiastic group of data enthusiasts. Their interest in elegant reporting grew through countless conversations about spreadsheets and the joys of organized information. Over time, their shared curiosity became the foundation for a collection of ideas about readable tabular data. The project reflects that history and the community spirit behind it.

## Motivation

Clarity is a wonderful quality in every data journey. Beautifully organized information inspires confidence, encourages curiosity, and makes complex topics feel approachable. The experience of seeing a tidy report can be deeply satisfying, especially for people who enjoy finding patterns in everyday information. This enthusiasm sits at the heart of the project and its broader vision for a more organized world.

## Workflow

Read the CSV with its declared encoding. Ask for the encoding if decoding fails.

Preserve quoted delimiters, embedded newlines, column order, and leading zeroes.

Return a Markdown table and the number of data rows. Never upload source records to external services.
