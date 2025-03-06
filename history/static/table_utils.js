function td(text, link, tooltip, onclick) {
	const td = document.createElement('td')
	if(link) {
		td.appendChild(make_link(text, link, onclick))
	} else if(tooltip) {
		td.appendChild(make_tooltip(tooltip, text))
	} else {
		td.textContent = text
	}
	return td
}

function make_tooltip(title, text) {
	const a = document.createElement('a')
	if(title) a.title = title
	a.textContent = text
	return a
}

function make_link(text, link, onclick = null) {
	const a = document.createElement('a')
	a.href = link
	a.textContent = text
	if(onclick) a.addEventListener('click', (e) => {
		e.preventDefault()
		e.stopPropagation()
		onclick()
		return false
	})
	return a
}

function make_small(text, title = null) {
	const small = document.createElement('small')
	small.textContent = text
	if(title) small.title = title
	return small
}