#!/bin/bash
# Quick script to find your Supabase anon key

echo "======================================"
echo "FINDING YOUR SUPABASE ANON KEY"
echo "======================================"
echo ""
echo "Option 1: Check browser at your project"
echo "  Go to: https://supabase.com/dashboard/project/xqvloyzxygcujfqdfwpr/settings/api"
echo "  Look for 'anon public' key"
echo ""
echo "Option 2: Use CLI"
echo "  Run: supabase projects api-keys --project-ref xqvloyzxygcujfqdfwpr"
echo ""
echo "Option 3: If running locally"
echo "  Check: ~/.supabase/access-token"
echo "  Or check: supabase status"
echo ""
echo "Paste the key here when found (starts with eyJ...):"
read SUPABASE_KEY

if [[ $SUPABASE_KEY == eyJ* ]]; then
    echo "SUPABASE_KEY=$SUPABASE_KEY" >> .env
    echo "✅ Key added to .env!"
    echo ""
    echo "Now run: ./launch_dashboard.sh"
else
    echo "❌ That doesn't look like a valid key (should start with eyJ)"
fi
