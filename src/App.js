import React, { Component } from 'react';
import {OrderedMap, Map} from 'immutable';
import './App.css';
import {me, members} from './Data.js';
import AvatarField from './containers/AvatarField.js';
import NavMenu from './components/NavMenu.js';
import Sockette from 'sockette';


class App extends Component {
    static defaultProps = {
       members: members
    }

    constructor(props){
        super(props);

        this.onMove = this.onMove.bind(this);
        this.onWSOpen = this.onWSOpen.bind(this);
        this.onWSClose = this.onWSClose.bind(this);
        this.onWSError = this.onWSError.bind(this);
        this.onMessage = this.onMessage.bind(this);
        this.updatePosition = this.updatePosition.bind(this);

        const memberMap = props.members.reduce((acc, cur, i) => {
            return acc.set(cur.user.id, Map(cur));
        }, OrderedMap());

        this.state = {
            members: memberMap,
            locked: true,
            sid: this.getSID()
        };
    }

    // a random number, sent to the websocket, so we don't get our own
    // messages reflected back at us. Unique only to this open webpage
    getSID() {
        return Math.floor(Math.random() * Math.floor(1000000));
    }

    componentDidMount() {
        const ws = new Sockette(`ws://localhost:5000/ws?sid=${this.state.sid}`, {
            onopen: this.onWSOpen,
            onerror: this.onWSError,
            onclose: this.onWSClose,
            onmessage: this.onMessage
        });
        this.setState({ws});
    }

    onWSOpen(e) {
        this.setState({locked: false});
    }

    onWSClose(e) {
        this.setState({locked: true});
    }

    onWSError(e) {
        this.setState({locked: true});
        console.log(e);
    }

    updatePosition(userID, position) {
        this.setState((oldState, props) => {
            oldState.members = oldState.members.withMutations((map) => {
                const user = map.get(userID);
                map.delete(userID);
                map.set(userID, user.set('position', position));
            });
            return oldState;
        });

    }

    onMove(userID, position) {
        this.updatePosition(userID, position);
        this.state.ws.json({userID, position});
    }

    onMessage(e) {
        const {userID, position} = JSON.parse(e.data);
        this.updatePosition(userID, position);
    }

    render() {
        return (
            <div className="App">
                <NavMenu user={me} />
                <AvatarField
            user={me}
            icons={this.state.members}
            avatarSize="64"
            onMove={this.onMove}
            locked={this.state.locked}
                />
            </div>
        );
    }
}

export default App;
