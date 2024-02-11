import { Card } from 'antd';
import React, { useEffect, useState } from 'react';

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
      <p>{lastMessage}</p>
    </Card>
  );
}

export default SimpleReceiver;
