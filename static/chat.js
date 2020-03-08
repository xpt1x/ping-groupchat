document.addEventListener('DOMContentLoaded', () => {

    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port + '/')
    var send_clicked = false

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
        let container = document.querySelector('#chat-box')
        container.scrollTop = (container.scrollHeight + container.offsetHeight);
    })

    socket.on('on user join', data => {
        const li = document.createElement('li')
        li.classList.add('list-group-item')
        li.innerHTML = `<strong>${data.user_name}</strong> has joined the channel`
        
        document.querySelector('#chat-box').append(li)
        let container = document.querySelector('#chat-box')
        container.scrollTop = (container.scrollHeight + container.offsetHeight);
    })

    socket.on('left announce', data => {

        const li = document.createElement('li')
        li.classList.add('list-group-item')
        li.innerHTML = `<strong>${data.user_name}</strong> has left the channel`
        document.querySelector('#chat-box').append(li)

        let container = document.querySelector('#chat-box')
        container.scrollTop = (container.scrollHeight + container.offsetHeight);
    })

    socket.on('destroy announce', data =>{
        window.alert('Channel Destroyed')
        window.location.replace('/leave')
    })
})
