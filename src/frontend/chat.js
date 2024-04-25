let userId;

function startChat() {
  userId = document.getElementById('user-id').value;
  // Hide the User ID section
  document.getElementById('chat-container').innerHTML = `
      <h2>Chat</h2> 
      <div id="chat-box"></div> 
      <input type="text" id="message-input">
      <button onclick="sendMessage()">Send</button>
    `;
}

function sendMessage() {
  const message = document.getElementById('message-input').value;
  document.getElementById('message-input').value = '';

  // Display user message
  displayMessage('You', message);

  // Send POST request to your Gen AI API endpoint 
  console.log('userId', userId, 'message', message);
  const response = fetch('https://crystaldroids-api-k7ji6xt3vq-ez.a.run.app/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, message: message })
  })
  const data = response.json()
  console.log(data)

  // Display AI response
  displayMessage('AI', data);
}

function displayMessage(sender, message) {
  const chatBox = document.getElementById('chat-box');
  chatBox.innerHTML += `
      <p><strong>${sender}:</strong> ${message}</p> 
    `;
}