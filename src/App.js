import React, { Component } from 'react';
import './App.css';
import {me, members} from './Data.js';
import Draggable from 'react-draggable';
import Sockette from 'sockette';

class AvatarField extends Component {
    static defaultProps = {
        onMoveStart: (av) => {},
        onMoveEnd: (av) => {},
        onMove: (av) => {},
        locked: true
    }

    constructor(props) {
        super(props);
        this.state = {
            icons: props.icons,
            avatarSize: props.avatarSize
        };

        this.onSizeChange = this.onSizeChange.bind(this);
    }

    onSizeChange(newSize) {
        this.setState({avatarSize: newSize});
    }

    // Move whatever avatar has just been moved to the top of the stack
    onMoveStart(av, e, dd) {
        this.setState((oldState, props) => {
            var idx = oldState.icons.indexOf(av);
            oldState.icons.splice(idx, 1);
            oldState.icons.push(av);
            return oldState;
        });
        this.props.onMoveStart(av);
    }

    onMoveEnd(av, e, dd) {
        this.props.onMoveEnd(av);
    }

    onMove(av, e, dd) {
        this.setState((oldState, props) => {
            var idx = oldState.icons.indexOf(av);
            oldState.icons[idx].position = {x: dd.x, y: dd.y};
            return oldState;
        });
        console.log(this.state.icons);
        this.props.onMove(av);
    }

    render() {
        const avatars = this.state.icons.map(
            (avatar) =>
                <Draggable
            defaultPosition={avatar.position}
            onStart={this.onMoveStart.bind(this, avatar)}
            onDrag={this.onMove.bind(this, avatar)}
            onEnd={this.onMoveEnd.bind(this, avatar)}
            bounds="parent"
            disabled={this.props.locked}
            key={avatar.user.id}
                >
                <UserAvatar user={avatar.user} size={this.state.avatarSize}/>
                </Draggable>
        );
        return (
            <div>
                <SizeSelector value={this.state.avatarSize} min="32" max="128"
            onSizeChange={this.onSizeChange}/>
                <div id="avatar-field">
                {avatars}
                </div>
           </div>
        );
    }
}

class SizeSelector extends Component {
    static defaultProps = {
        onSizeChange: (v) => {}
    }
    constructor(props) {
        super(props);
        this.state = {
            value: props.value
        };
        this.onChange = this.onChange.bind(this);
    }

    onChange(e) {
        var value = e.target.value;
        this.setState({value: value});
        e.stopPropagation();
        e.preventDefault();

        this.props.onSizeChange(value);
    }

    render() {
        return (
                <input type="range"
            value={this.state.value}
            min={this.props.min}
            max={this.props.max}
            onChange={this.onChange}/>
        );
    }
}

class AvatarMenu extends Component {
    render() {
        return (
            <div id="avatar-menu">
                <UserAvatar user={this.props.user} />
            </div>
        );
    }
}

class UserAvatar extends Component {
    render() {
        const {user, ...others} = this.props;
        return (
                <DiscordImage
            {...others}
            baseURL="https://cdn.discordapp.com/avatars/"
            objectID={user.id}
            imageID={user.avatar}
            altText={user.username}
                />
        );
    }
}

class DiscordImage extends Component {
    render() {
        var {
            objectID,
            imageID,
            baseURL,
            altText,
            className,
            size,
            ...others
        } = this.props;
        const imageSize = Math.pow(2, Math.round(Math.log2(size)));
        const url = `${baseURL}${objectID}/${imageID}.png?size=${imageSize}`;
        return (
                <img {...others}
            src={url} height={size} width={size}
            className={className + " icon "}
            alt={this.props.altText}
                />
        );
    }
}

class App extends Component {
    constructor(props){
        super(props);

        this.onMove = this.onMove.bind(this);
        this.onWSOpen = this.onWSOpen.bind(this);
        this.onWSClose = this.onWSClose.bind(this);
        this.onWSError = this.onWSError.bind(this);
        this.onMessage = this.onMessage.bind(this);

        this.state = {
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

    onMove(user) {
        user.sid = this.state.sid;
        this.state.ws.json(user);
    }

    onMessage(e) {
        console.log(e);
    }

    render() {
        return (
            <div className="App">
                <AvatarMenu user={me} />
                <AvatarField
                    icons={members}
                    avatarSize="64"
                    onMove={this.onMove}
                    locked={this.state.locked}
                />
            </div>
        );
    }
}

export default App;
