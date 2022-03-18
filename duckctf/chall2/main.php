<?php
  if (empty($_GET['id'])) {
    ?>
    <h2>List of news</h2>
    <table>
      <tr>
        <th>Id</th>
        <th>Title</th>
        <th>Author</th>
        <th>Date</th>
      </tr>
      <?php
        $news = get_news();
        while ($row = $news->fetch_assoc()) {
          echo "<tr onClick=\"window.location.href = '/?id=" . $row['id'] . "'\">";
          echo "<td>" . $row['id'] . "</td>";
          echo "<td>" . htmlentities($row['title']) . "</td>";
          echo "<td>" . htmlentities($row['author']) . "</td>";
          echo "<td>" . $row['date_created'] . "</td>";
          echo "</tr>";
        }
      ?>
    </table>
    <?php
  } else {
    $news = get_news_id($_GET['id']);
    if ($news->{"num_rows"}) {
      $row = $news->fetch_assoc();
      echo "<h2>Article: " . htmlentities($row['title']) . "</h2>";
      echo "<h5>Author: " . htmlentities($row['author']) . " - Date: " . $row['date_created'] . "</h5>";
      echo "<br /><br />";
      echo "<pre>" . htmlentities($row['content']) . "</pre>";
      echo "<br /><hr />";
      echo '<input type="button" onclick="location.href=\'?id=' . $row['id'] . '&action=update\';" value="Update" />&nbsp;';
      echo '<input type="button" onclick="location.href=\'?id=' . $row['id'] . '&action=delete\';" value="Delete" />';
    } else {
      echo "<h3 style='color:red;'> Article not found </h3>";
    }
  }
?>