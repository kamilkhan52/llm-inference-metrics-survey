#!/bin/bash
# Fetch arXiv PDFs for full-read papers in SELECTION.tsv into fulltext/, convert to text. Polite: 3 s between downloads.
P=.
PRIOR=<prior-project>/fulltext
cd "$P"
awk -F'\t' 'NR>1 && ($6=="full"||$6=="mp-full") && $2!="" {print $2}' SELECTION.tsv | while read id; do
  f=fulltext/arxiv_${id}.pdf
  if [ ! -s "$f" ] && [ -s "$PRIOR/arxiv_${id}.pdf" ]; then cp "$PRIOR/arxiv_${id}.pdf" "$f"; echo "copied $id"; fi
  if [ ! -s "$f" ]; then
    curl -sL -A "Mozilla/5.0 (research survey)" -o "$f" "https://arxiv.org/pdf/${id}"
    sleep 3
  fi
  if head -c 4 "$f" | grep -q '%PDF'; then
    [ -s "fulltext/arxiv_${id}.txt" ] || pdftotext -layout "$f" "fulltext/arxiv_${id}.txt" 2>/dev/null
    echo "ok $id $(wc -l < fulltext/arxiv_${id}.txt)"
  else
    echo "FAIL $id"; rm -f "$f"
  fi
done
echo DONE
