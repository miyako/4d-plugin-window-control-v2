$path:=Get 4D folder:C485(Current resources folder:K5:16)+"sample.png"

READ PICTURE FILE:C678($path;$icon)

WINDOW SET ICON (Current form window:C827;$icon)


Form:C1466.icon:=WINDOW Get icon (Current form window:C827)