echo off
echo Generating UI Files
echo on
for %%F in (memorise/ui/*.ui) do pyuic5 -o memorise/ui/ui%%~nF.py memorise/ui/%%F