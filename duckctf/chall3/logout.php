<?php
  session_start();
  setcookie(session_id(), "", time() - 3600);
  session_unset();
  session_destroy();
  session_write_close();
  header('Location: index.php');
?>
