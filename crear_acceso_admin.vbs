Set oWS = WScript.CreateObject("WScript.Shell")
sDesk = oWS.SpecialFolders("Desktop")
sDir = oWS.CurrentDirectory
Set oLink = oWS.CreateShortcut(sDesk & "\Sistema Inventario - Administrador.lnk")
oLink.TargetPath = sDir & "\iniciar_administrador.bat"
oLink.WorkingDirectory = sDir
oLink.IconLocation = sDir & "\icono_administrador.ico,0"
oLink.Save
