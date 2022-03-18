<?php
  if (empty($_GET['id'])) {
    echo "<h3 style='color:red;'>Empty Id</h3>";
  } else {
    $news = get_news_id($_GET['id']);
    if ($news->{"num_rows"} === 0) {
      echo "<h3 style='color:red;'>Article not found</h3>";
      die();
    }
    delete_news($_GET['id']);
    header("location: index.php");
    die();
  }
?>