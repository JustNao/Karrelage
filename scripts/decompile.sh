#!/bin/sh

export DofusInvoker="C:\Users\USERNAME\AppData\Local\Ankama\Dofus\DofusInvoker.swf"
export selectclass='com.ankamagames.dofus.BuildInfos,com.ankamagames.dofus.network.++,com.ankamagames.jerakine.network.++'
export config='parallelSpeedUp=0'

cd "$( dirname "${BASH_SOURCE[0]}" )"
cd ..

"C:\Program Files (x86)\FFDec\ffdec.exe" \
  -config "$config" \
    -selectclass "$selectclass" \
      -export script \
        ./protocol $DofusInvoker
