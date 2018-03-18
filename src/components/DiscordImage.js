import React, { Component } from 'react';

import './DiscordImage.css';

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
            className={className + " icon"}
            alt={this.props.altText}
                />
        );
    }
}

export default DiscordImage;
