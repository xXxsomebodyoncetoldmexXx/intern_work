<?php
$g = imagecreatefromgif("./payload.php.gif");
echo $g;
imagegif($g, "./final.php.gif");
imagedestroy($g);
?>
