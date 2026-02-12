#!/bin/bash
echo "=== Diagnostic Control Web ==="
echo ""

echo "1. Version Python:"
python3 --version
echo ""

echo "2. Chemin Python:"
which python3
echo ""

echo "3. Test import symbol:"
python3 -c "import symbol; print('✅ Module symbol OK')" 2>&1
echo ""

echo "4. Test import Flask:"
python3 -c "import flask; print('✅ Flask OK')" 2>&1
echo ""

echo "5. Modules installés:"
pip3 list | grep -E "Flask|gunicorn"
echo ""

echo "6. Contenu du répertoire:"
ls -la /home/Server-Control-Panel-V2/flask-template/
echo ""

echo "7. Test import controlWeb:"
cd /home/Server-Control-Panel-V2/flask-template
python3 -c "from controlWeb import controlWeb; print('✅ Import controlWeb OK')" 2>&1
echo ""

echo "8. Derniers logs du service:"
sudo journalctl -u controlWeb.service -n 20 --no-pager