import React, { useEffect, useState } from 'react';
import { Card } from 'antd';

const SimpleReceiver = ({ payload }) => {
  const [lastMessage, setLastMessage] = useState();

  useEffect(() => {
    if (payload.topic) {
      setLastMessage(payload.message)
    }
  }, [payload])

  return (
    <Card
      title="Last Msg Receiver"
    >
      <h1>{lastMessage}</h1>
    </Card>
  );
}

export default SimpleReceiver;
