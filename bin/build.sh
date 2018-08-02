BINDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
BASEDIR="$BINDIR/.."

rm -rf $BASEDIR/dist

python3 setup.py sdist bdist_wheel