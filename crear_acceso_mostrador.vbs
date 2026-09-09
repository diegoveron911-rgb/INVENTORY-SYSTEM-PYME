Set oWS = WScript.CreateObject("WScript.Shell")
sDesk = oWS.SpecialFolders("Desktop")
sDir = oWS.CurrentDirectory
Set oLink = oWS.CreateShortcut(sDesk & "\Sistema Inventario - Mostrador.lnk")
oLink.TargetPath = sDir & "\iniciar_mostrador.bat"
oLink.WorkingDirectory = sDir
oLink.IconLocation = sDir & "\icono_mostrador.ico,0"
oLink.Save
