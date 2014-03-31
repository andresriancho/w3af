<?php
//
// router.php
//
// http://www.php.net/manual/en/features.commandline.webserver.php
// Example #5 Handling Unsupported File Types
//
$path = pathinfo($_SERVER["SCRIPT_FILENAME"]);
if ($path["extension"] == "swf") {
    header("Content-Type: application/x-shockwave-flash");
    readfile($_SERVER["SCRIPT_FILENAME"]);
}
else {
    return FALSE;
}
?>