#!/bin/bash
curl -H "Content-Type:plain/text" "http://localhost:8222/suffer" -d "$*"
echo ""
exit 0
