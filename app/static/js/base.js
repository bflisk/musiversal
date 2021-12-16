const d = document
const a = d.getElementsByTagName('a');

if(d.URL.includes('view_playlist')) {
  for(let i = 0; i < a.length; i++) {
    if(a[i].innerHTML === '+') {
      a[i].style.visibility = 'hidden';
    };
  };
} else if(d.URL.includes('view_blacklist')) {
  console.log('meow')
  for(let i = 0; i < a.length; i++) {
    if(a[i].innerHTML === 'x') {
      a[i].style.visibility = 'hidden';
    };
  };
};
