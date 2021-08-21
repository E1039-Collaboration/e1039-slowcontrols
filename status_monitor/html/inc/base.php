<?php

$utime_now = time();
$num_prob = 0;
$num_warn = 0;

function IncludeStatus($fn_html)
{
  global $utime_now, $num_prob, $num_warn;
  if (! file_exists('sub/'.$fn_html)) {
    $title = str_replace('.html', '' , $fn_html);
    $title = str_replace('_'    , ' ', $title);
    echo '<span class="header warning">',$title,'</span>';
    echo '<p>Not Implemented.</p>';
    $num_warn++;
  } else {
    $cont = file_get_contents('sub/'.$fn_html);
    echo $cont;
    $num_prob += substr_count($cont, "<tr class='problem'>");
    $num_warn += substr_count($cont, "<tr class='warning'>");

    $time = $utime_now - filemtime('sub/'.$fn_html);
    $class = 'normal';
    if      ($time > 130) { $class = 'problem'; $num_prob++; }
    else if ($time >  70) { $class = 'warning'; $num_warn++; }
    echo '<div class="',$class,'">',$time,' sec from last update.</div>';
  }
  echo "<hr>\n";
}

function ShowProblem()
{
  global $utime_now, $num_prob, $num_warn;
  //echo     '<span class="',($num_prob > 0 ? 'problem' : 'normal'),'">Total <i>N</i> of problems = ',$num_prob,'.</span>';
  //echo '<br><span class="',($num_warn > 0 ? 'warning' : 'normal'),'">Total <i>N</i> of warnings = ',$num_warn,'.</span>';
  echo '<div>Total <i>N</i> of problems = ',$num_prob,'.</div>';
  echo '<div>Total <i>N</i> of warnings = ',$num_warn,'.</div>';
  if ($num_prob > 0) {
    //echo ' <span>An audible alarm is issued once per minute.  If you do not hear it, please check if your web browser is blocking the audio autoplay.</span>';
    if ($utime_now % 60 < 10) {
      echo '<audio src="sound/voice_problem.mp3" autoplay></audio>';
    }
  }
  echo '<div><a href="help.php">Help Page</a></div><hr>';
}

?>
