<?php
  if (empty($_GET['id'])) {
    echo "<h3 style='color:red;'>Empty Id</h3>";
  } else {
    $news = get_news_id($_GET['id']);
    if ($news->{"num_rows"} === 0) {
      echo "<h3 style='color:red;'>Article not found</h3>";
      die();
    }
    $row = $news->fetch_assoc();

    if ($_SERVER['REQUEST_METHOD'] === 'GET') {
        echo "
        <form id=\"add-form\" method=\"POST\">
          Title
          <br />
          <input type=\"text\" name=\"title\" placeholder='" . htmlentities($row['title']) . "'>
          <br />
          <br />
          Content
          <br />
          <textarea name=\"content\" cols=\"30\" rows=\"10\" placeholder='" . htmlentities($row['content']) . "'></textarea>
          <br />
          <br />
          <button type=\"submit\">Submit</button>
        </form>
        ";
    } elseif ($_SERVER['REQUEST_METHOD'] === 'POST') {
      $title = empty($_POST['title']) ? $row['title'] : $_POST['title'];
      $content = empty($_POST['content']) ? $row['content'] : $_POST['content'];
      update_news($row['id'], $title, $content);
      header("location: /?id=" . $row['id']);
      die();
    }
  }
?>