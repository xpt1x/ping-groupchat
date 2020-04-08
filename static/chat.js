document.addEventListener('DOMContentLoaded', () => {

    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port + '/')
    var send_clicked = false

    function ScrollToBottom() {
        let container = document.querySelector('#chat-box')
        container.scrollTop = (container.scrollHeight + container.offsetHeight);
    }

    function GetUsername() {
        var user_name = null
        const request = new XMLHttpRequest()
        request.open('GET', '/user', false)
        request.onload = () => {
            const response = JSON.parse(request.responseText)
            if(response.status == 200) {
                user_name = response.name
            }
        }
        request.send()
        return user_name
    }

    socket.on('connect', () => {
        // let server know user has joined channel
        socket.emit('user joined')
        document.querySelector('#send-btn').disabled = true;
        
    })
    // emulating Enter key
    document.querySelector('#input-text').addEventListener('keydown', event => {
        if (event.which == 13) {
            document.querySelector('#send-btn').click()
        }
    })
    // disable on empty message
    document.querySelector('#input-text').onkeyup = () => {
        if (document.querySelector('#input-text').value.length > 0) {
            document.querySelector('#send-btn').disabled = false;
            if (document.querySelector('#typing-box').innerHTML == '')
                socket.emit('user typing')
            }
        else {
            document.querySelector('#send-btn').disabled = true;
            if (document.querySelector('#typing-box').innerHTML != '')
                socket.emit('typing cleared')
        }
    };

    document.querySelector('#send-btn').onclick = () => {
        let time = new Date;
        time = time.toLocaleTimeString();
        send_clicked = true
        socket.emit('send message', {'msg': document.querySelector('#input-text').value, 'time': time})    
        return false
    }

    document.querySelector('#leave-btn').onclick = () => {
        socket.emit('user left') 
        window.location.replace('/leave')
    }

    if (document.getElementById("destroy-btn")) {
        document.querySelector('#destroy-btn').onclick = () => {
            socket.emit('channel destroy clicked')
            window.location.replace('/leave')
        }
    }

    if (document.getElementById("prune-btn")) {
        document.querySelector('#prune-btn').onclick = () => {
            socket.emit('chat prune clicked')
        }
    }

    if(document.getElementById("ban-modal-btn")) {

        document.querySelector('#ban-modal-btn').onclick = () => {
            const request = new XMLHttpRequest()
            request.open('GET', `/userinfo/${document.getElementById("ban-modal-btn").value}`)
            request.onload = () => {
                const response = JSON.parse(request.responseText)

                if(response.status == 200) {
                    document.getElementById("ban-options").innerHTML = ''
                    response.users.forEach(name => {
                        var option = document.createElement('option')
                        option.value = option.innerHTML = name
                        document.getElementById("ban-options").appendChild(option)
                    });
                    document.getElementById('ban-options').disabled = false
                    document.getElementById('ban-btn').disabled = false
                }
                else {
                    document.getElementById("ban-options").innerHTML = ''
                    document.getElementById('ban-options').disabled = true
                    document.getElementById('ban-btn').disabled = true
                }
            }
            request.send()
            
        }

        document.querySelector('#ban-btn').onclick = () => {
            socket.emit('ban clicked', {'user': document.getElementById('ban-options').value})
        }
    }

    if(document.getElementById("unban-modal-btn")) {

        document.querySelector('#unban-modal-btn').onclick = () => {
            document.getElementById('loading').style.display = 'block'
            document.getElementById('unban-form').style.display = 'none'
            const request = new XMLHttpRequest()
            request.open('GET', `/bannedUsers/${document.getElementById("unban-modal-btn").value}`)
            
            request.onload = () => {
                const response = JSON.parse(request.responseText)
                // for loading 
                document.getElementById('loading').style.display = 'none'
                document.getElementById('unban-form').style.display = 'block'

                if(response.status == 200) {
                    document.getElementById('unban-label').innerHTML = 'Ban User'
                    document.getElementById("unban-options").innerHTML = ''
                    response.users.forEach(name => {
                        var option = document.createElement('option')
                        option.value = option.innerHTML = name
                        document.getElementById("unban-options").appendChild(option)
                    });
                    
                    document.getElementById('unban-options').disabled = false
                    document.getElementById('unban-btn').disabled = false
                }
                else {
                    document.getElementById("unban-options").innerHTML = ''
                    document.getElementById('unban-label').innerHTML = 'No Users to unban'
                    document.getElementById('unban-options').disabled = true
                    document.getElementById('unban-btn').disabled = true
                }
            }
            request.send()
        }

        document.querySelector('#unban-btn').onclick = () => {
            socket.emit('unban clicked', {'user': document.getElementById('unban-options').value})
        }
    }

    socket.on('user is typing', data => {
        document.querySelector('#typing-box').innerHTML = `${data['user']} is typing...`
    })

    socket.on('clear typing box', () => {
        document.querySelector('#typing-box').innerHTML = ''
    })

    socket.on('recieved message', data => {
        const li = document.createElement('li')
        // If send by self
        if (send_clicked) {
            // additional styling
            li.classList.add('list-group-item')
            li.classList.add('list-group-item-dark')
            // setting user's fields to original state
            document.querySelector('#input-text').value = ''
            send_clicked = false
        }
        else
            li.classList.add('list-group-item')
        
        li.innerHTML = data.form_msg + `<span id="time" style="float: right;" class="badge badge-secondary badge-pill">${data.time}</span>`
        document.querySelector('#chat-box').append(li)
            
        document.querySelector('#send-btn').disabled = true;
        socket.emit('typing cleared')

        // scrolling to bottom
        ScrollToBottom()
    })

    socket.on('on user join', data => {
        var div = document.getElementById('online-users')
        while(div.hasChildNodes()) {
            div.removeChild(div.firstChild)
        }
        const li = document.createElement('li')
        data.users.forEach(user => {
            const a = document.createElement('a')
            a.id = `user-${user}`
            a.classList.add('dropdown-item')
            a.innerHTML = user
            document.getElementById('online-users').appendChild(a)
        });
        
        li.classList.add('list-group-item')
        li.innerHTML = `> User <strong>${data.user_name}</strong> has joined the channel`

        document.querySelector('#chat-box').append(li)
        ScrollToBottom()
    })

    socket.on('left announce', data => {

        const li = document.createElement('li')
        li.classList.add('list-group-item')
        li.innerHTML = `> User <strong>${data.user_name}</strong> has left the channel`
        
        var div = document.getElementById('online-users')
        while(div.hasChildNodes()) {
            div.removeChild(div.firstChild)
        }

        data.users.forEach(user => {
            const a = document.createElement('a')
            a.id = `user-${user}`
            a.classList.add('dropdown-item')
            a.innerHTML = user
            document.getElementById('online-users').appendChild(a)
        });

        document.querySelector('#chat-box').append(li)
        ScrollToBottom()
    })

    socket.on('destroy announce', data =>{
        window.alert('Channel Destroyed')
        window.location.replace('/leave')
    })

    socket.on('prune announce', data =>{
        document.querySelector('#chat-box').innerHTML = ''
        const li = document.createElement('li')
        li.classList.add('list-group-item')
        li.innerHTML = `> Owner <strong>${data.user_name}</strong> has pruned the chat`

        document.querySelector('#chat-box').append(li)
        ScrollToBottom()
    })

    socket.on('user banned', data => {
        if(GetUsername() == data.user) {
            window.alert('You have been banned from this channel by ' + data.by)
            window.location.replace('/leave')
        }

        var div = document.getElementById('online-users')
        for (var i=0; i<div.childNodes.length; i++) {
            var child = div.childNodes[i];
            if (child.innerHTML == data.user) {
                div.removeChild(child)
                break
            }
          }

        const li = document.createElement('li')
        li.classList.add('list-group-item')
        li.innerHTML = `> Owner <strong>${data.by}</strong> has banned user: ${data.user}`

        document.querySelector('#chat-box').append(li)
        ScrollToBottom()
    })

    socket.on('user unbanned', data => {
        const li = document.createElement('li')
        li.classList.add('list-group-item')
        li.innerHTML = `> Owner <strong>${data.by}</strong> has unbanned user: ${data.user}`
        document.querySelector('#chat-box').append(li)
        ScrollToBottom()
    })
})
