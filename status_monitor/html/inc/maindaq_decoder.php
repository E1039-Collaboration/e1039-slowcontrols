<?php

include '/var/www/html/data-summary/e1039/inc/base.php';

function MainDaqDecoderSummary($sqlcon)
{
  global $utime_now, $num_prob, $num_warn;

  $comm = "select * from deco_error_info order by run_id desc limit 1";
  $result = mysql_query($comm, $sqlcon) or die("!!ERROR!!  Failed in executing query: ".$comm);
  $row = mysql_fetch_assoc($result);
  $run       = $row['run_id'];
  $spill     = $row['spill_id'];
  $utime     = $row['utime'];
  $n_evt_all = $row['n_evt_all'];
  $n_evt_ng  = $row['n_evt_ng' ];

  $list_deco_status = array('', 'Started', 'Finished', 'Updated');
  $comm = "select deco_status from deco_status where run_id = ".$run;
  $result = mysql_query($comm, $sqlcon) or die("!!ERROR!!  Failed in executing query: ".$comm);
  $row = mysql_fetch_array($result);
  $deco_status = $row[0];
  $deco_status_str = $list_deco_status[ $deco_status ];

  echo 'Last Updated: ',date("Y-m-d H:i:s", $utime),"\n",
       "<table>\n",
       '<tr><td>Run</td><td>',$run,"</td></tr>\n",
       '<tr><td>Decoder status</td><td>',$deco_status_str,"</td></tr>\n",
       '<tr><td>Last spill</td><td>',$spill,"</td></tr>\n",
       '<tr><td><i>N</i> of all flush events</td><td>',$n_evt_all,"</td></tr>\n";
  $class = 'normal';
  if ($deco_status != 2 && $n_evt_all > 5000) {
    if      ($n_evt_ng / $n_evt_all > 0.10) { $class = 'problem'; $num_prob++; }
    else if ($n_evt_ng / $n_evt_all > 0.01) { $class = 'warning'; $num_warn++; }
  }
  echo '<tr class="',$class,'"><td><i>N</i> of bad flush events</td><td>',$n_evt_ng,"</td></tr>\n";

  $comm = "select coalesce(max(error_count), 0), count(*) from deco_error_tdc where run_id = ".$run;
  $result = mysql_query($comm, $sqlcon) or die("!!ERROR!!  Failed in executing query: ".$comm);
  $row = mysql_fetch_array($result);
  $n_err_max  = $row[0];
  $n_err_type = $row[1];

  $class = 'normal';
  if      ($n_err_max / $n_evt_all > 0.10) { $class = 'problem'; $num_prob++; }
  else if ($n_err_max / $n_evt_all > 0.01) { $class = 'warning'; $num_warn++; }
  echo '<tr class="',$class,'"><td>Max <i>N</i> of TDC error counts</td><td>',$n_err_max,"</td></tr>\n";
  echo '<tr><td><i>N</i> of TDC error types</td><td>',$n_err_type,"</td></tr>\n";

  echo "</table>\n";

  $time = $utime_now - $utime;
  $class = 'normal';
  if ($deco_status != 2) {
    if      ($time > 130) { $class = 'problem'; $num_prob++; }
    else if ($time >  70) { $class = 'warning'; $num_warn++; }
  }
  echo '<div class="',$class,'">',$time,' sec from last update.</div>';
}

function MainDaqDecoderPanel()
{
  echo "<div class='header'>MainDAQ Decoder Status</div>\n";
  MakeConnection($sqlcon, $server);
  SelectDB('user_e1039_maindaq', $sqlcon);
  MainDaqDecoderSummary($sqlcon);
  echo '<a href="detail_maindaq_decoder.php">Detail Page</a>';
  echo "<hr>\n";
}

?>
