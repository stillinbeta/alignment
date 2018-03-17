import React, { Component } from 'react';
import './App.css';
import './Slider.css';
import {me, members} from './Data.js';
import Draggable from 'react-draggable';
import Sockette from 'sockette';

class AvatarField extends Component {
    static defaultProps = {
        onMoveStart: (av) => {},
        onMoveEnd: (av) => {},
        onMove: (av) => {},
        locked: true,
        background: "/default-background.png",
        backgroundHeight: 680,
        backgroundWidth: 675
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
            onStart={this.onMoveStart.bind(this, avatar)}
            onDrag={this.onMove.bind(this, avatar)}
            onEnd={this.onMoveEnd.bind(this, avatar)}
            bounds="parent"
            defaultPosition={avatar.position}
            disabled={this.props.locked}
            key={avatar.user.id}
                >
                <UserAvatar user={avatar.user} size={this.state.avatarSize}/>
                </Draggable>
        );

        const background = {
            backgroundImage: `url(${this.props.background})`,
            height: `${this.props.backgroundHeight}px`,
            width: `${this.props.backgroundWidth}px`
        };

        return (
            <div>
                <SizeSelector value={this.state.avatarSize} user={me} min="32" max="128"
            onSizeChange={this.onSizeChange}/>
                <div id="avatar-field" style={background}>
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
            <div className="size-selector-container">

                <div className="size-example-small">
                    <UserAvatar className="" size={this.props.min} user={this.props.user} />
                </div>
                <div className="slider-box">
                        <input type="range"
                    value={this.state.value}
                    min={this.props.min}
                    max={this.props.max}
                    onChange={this.onChange}
                    className="size-selector"
                        />
                </div>

                <div className="size-example-large">
                    <UserAvatar className="size-example-large" size={this.props.max} user={this.props.user} />
                </div>
            </div>
        );
    }
}

class BackgroundSelector extends Component {
    static defaultProps = {
        value: "",
        placeHolder: "https://elly.dog",
        onSubmit: (val) => {}
    }

    constructor(props) {
        super(props);
        this.state = {
            value: props.value
        };

        this.onChange = this.onChange.bind(this);
        this.onSubmit = this.onSubmit.bind(this);
    }

    onChange(e) {
        this.setState({value: e.target.value});
        e.preventDefault();
        e.stopPropagation();
    }

    onSubmit(e) {
        this.props.onSubmit(this.state.value);
        e.preventDefault();
        e.stopPropagation();
    }

    render() {
        return (
            <div className="upload-form">
                <input type="text" placeHolder={this.props.placeHolder} onChange={this.onChange}/>
                <a onClick={this.onSubmit}>Do the thing</a>
            </div>
        );
    }
}

class AvatarMenu extends Component {
    constructor(props) {
        super(props);
        this.state = {
            upload: false
        };

        this.newImage = this.newImage.bind(this);
        this.handleImage = this.handleImage.bind(this);

    }

    newImage() {
        this.setState({upload: true});
        console.log("new image time");
    }

    handleImage(imageURL) {
        this.setState({upload: false});
        console.log(imageURL);
    }

    render() {
        return (
            <nav>
                <a onClick={this.newImage}>New Image</a>
                { this.state.upload &&
                  <BackgroundSelector onSubmit={this.handleImage} />
                }
                <a href="/logout">Logout</a>
            </nav>
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
        const imageSize = Math.pow(2, Math.ceil(Math.log2(size)));
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
