document.addEventListener('DOMContentLoaded', () => {
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port)

    socket.on('connect', () => {
        // let server know user has joined channel
        socket.emit('user joined')
        document.querySelector('#send-btn').disabled = true;
        document.querySelector('#input-text').onkeyup = () => {
            if (document.querySelector('#input-text').value.length > 0)
                document.querySelector('#send-btn').disabled = false;
            else
                document.querySelector('#send-btn').disabled = true;
        };

        document.querySelector('#send-btn').onclick = () => {
            let time = new Date;
            time = time.toLocaleTimeString();
            socket.emit('send message', {'msg': document.querySelector('#input-text').value, 'time': time})     
            return false
        }
    })

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
    

    socket.on('recieved message', data => {
        const li = document.createElement('li')
        // If send by self
        if (localStorage.getItem('user_name') == data.by) {
            li.classList.add('list-group-item')
            li.classList.add('list-group-item-dark')
        }
        else
            li.classList.add('list-group-item')
    
        li.innerHTML = `<${data.time}> | <strong>${data.by}</strong>: ${data.msg}`
        document.querySelector('#chat-box').append(li)
        document.querySelector('#input-text').value = ''
        document.querySelector('#send-btn').disabled = true;

        // scrolling to bottom
        let container = document.querySelector('#chat-box')
        container.scrollTop = (container.scrollHeight + container.offsetHeight);
    })

    socket.on('on user join', data => {
        const li = document.createElement('li')
        li.classList.add('list-group-item')
        li.innerHTML = `<strong>${data.user_name}</strong> has joined the channel`
        // clear and add username to local
        localStorage.clear()
        localStorage.setItem('user_name', data.user_name)
        
        document.querySelector('#chat-box').append(li)
        let container = document.querySelector('#chat-box')
        container.scrollTop = (container.scrollHeight + container.offsetHeight);
    })

    socket.on('left announce', data => {

        const li = document.createElement('li')
        li.classList.add('list-group-item')
        li.innerHTML = `<strong>${data.user_name}</strong> has left the channel`
        localStorage.clear()
        document.querySelector('#chat-box').append(li)

        let container = document.querySelector('#chat-box')
        container.scrollTop = (container.scrollHeight + container.offsetHeight);
    })

    socket.on('destroy announce', data =>{
        window.alert('Channel Destroyed')
        window.location.replace('/leave')
    })
})