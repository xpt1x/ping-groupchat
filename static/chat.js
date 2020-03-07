document.addEventListener('DOMContentLoaded', () => {
    // namespace
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port + '/')

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
                socket.emit('user typing', {'user': document.querySelector('#user_id').innerHTML})
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
        if (data.by == document.querySelector('#user_id').innerHTML) {
            li.classList.add('list-group-item')
            li.classList.add('list-group-item-dark')
        }
        else
            li.classList.add('list-group-item')
    
        if (document.querySelector('#creator').innerHTML == data.by)
            li.innerHTML = `<${data.time}> | <strong style='color: #0388fc;'>${data.by}</strong>: ${data.msg}`
        else 
            li.innerHTML = `<${data.time}> | <strong>${data.by}</strong>: ${data.msg}`
        
        document.querySelector('#chat-box').append(li)
        // clear text field of user who sent the msg
        if (data.by == document.querySelector('#user_id').innerHTML)
            document.querySelector('#input-text').value = ''
            
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
