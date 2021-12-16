

/*$(document).ready(function loadTracks() {

});*/

// stops the addTracks async function from recalling before tracks are loaded
var addTracksFlag = false;

// gets a group of tracks from a set position
async function addTracks(offset, amount) {
  $.ajax({
    url: "/get_tracks/" + playlistId + "/" + offset + "/" + amount,
    type: "POST"
  })
  .done(function(tracks) {
    if(tracks != undefined) {
      assignTracks(tracks);
      addTracksFlag = false;
    };
  });
};

// assigns a list of tracks to their respective track beds
async function assignTracks(tracks) {
  for(let i = 0; i < tracks.length; i++) {
    // queries DOM for track bed
    trackBed = $('#track' + tracks[i]['track_pos']);

    if(trackBed.attr('class').includes('unloaded')) {
      // queries DOM for necessary elements
      trackArt = $(trackBed).find('.track-art')[0];
      trackInfo = $(trackBed).find('.track-info')[0];
      albumInfo = $(trackBed).find('.album-info')[0];
      artistList = $(trackBed).find('.artist-list');
      service = $(trackBed).find('.track-service');

      // assigns information to track beds
      trackArt.src = tracks[i]['art'];
      trackInfo.href = tracks[i]['href'];
      trackInfo.text = tracks[i]['title'];
      service.text = tracks[i]['service'];

      // assigns albums to tracks based on service
      if(tracks[i]['service'] == 'spotify') {
        albumInfo.href = tracks[i]['album']['href'];
        albumInfo.text = tracks[i]['album']['title'];
      } else if(tracks[i]['service'] == 'youtube') {
        albumInfo.href = '';
        albumInfo.text = '';
      };


      // assigns track artists, accounting for if there are multiple artists
      for(let j = 0; j < tracks[i]['artists'].length; j++) {
        artist = tracks[i]['artists'][j];
        artistElem = '<a class="artist-info" id="artist' + j + '" href="' + artist['href'] + '">' + artist['name'] + '  </a>';
        artistList.append(artistElem);
      };

      // identifies the track bed as loaded once it is finished loading
      trackBed.removeClass('unloaded');
      trackBed.addClass('loaded');
    };
  };
};

// returns the first element in the current viewport on scroll
$(function inViewport() {
  var table = $("#tracks");
  var rows = table.children();
  // var rows = table.children().children();

  $(document).scroll(function() {
      var scrollpos = $(document).scrollTop();
      var start = 0;
      var end = rows.length;
      var count = 0;

      while(start != end) {
          count++;
          var mid = start + Math.floor((end - start) / 2);
          if($(rows[mid]).offset().top < scrollpos)
              start = mid + 1;
          else
              end = mid;
      }

      $("#scrollpos").html("" + scrollpos);
      $("#first").html($($(rows[start]).children()[0]).html());
      $("#play-track-art").html($($(rows[start]).children()[0]).html());
      $("#count").html("" + count);

      // adds tracks to the browser as the user scrolls
      if(!addTracksFlag) {
        let pos = 0;

        // loops through visible elements and gets the position of the first unloaded element
        for(let k = 0; k < 15; k++) {
          let classes = $('#track' + (start + k)).attr('class');

          // having a class including unloaded indicated the first unloaded track
          if(classes.includes('unloaded')) {
            pos = start + k;

            addTracks(pos, 15);
            addTracksFlag = true;

            break;
          };
        };
      };
  });
});

// refreshes the playlist in the background
$('#refresh-playlist').click(async function() {
  $('#refresh-playlist').html("<img src='{{ url_for('static', filename='loading.gif') }}'>");

  $.ajax({
    url: "/refresh_playlist/" + playlistId,
    type: "POST"
  }).done(function(response) {
    $('#refresh-playlist').html("<a id='refresh-playlist'>Refresh Playlist</a>")
  });
});
