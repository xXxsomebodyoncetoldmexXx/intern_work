<?php 
if (empty($_GET['action'])){
  if (empty($_SESSION['login'])) {
    err("Please login to see messages");
  }
  include 'messages.php';
} elseif ($_GET['action'] === 'login') {
  include 'login.php';
} elseif ($_GET['action'] === 'register') {
  include 'register.php';
} elseif ($_GET['action'] === 'delete' && $_SESSION['isadmin']) {
  if (!empty($_GET['mid'])) {
    delete_msg($_GET['mid']);
    header("Location: /");
    die();
  } else {
    err("Missing message id");
  }
}
?>