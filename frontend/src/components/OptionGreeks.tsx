import React, { useState, useEffect } from 'react';
import { useQuery } from 'react-query';
import { Stack, DetailsList, IColumn, Text, SelectionMode, IDetailsListStyles } from '@fluentui/react';
import { optionDataProvider } from '../DataProvider/OptionDataProvider';

interface OptionGreeksProps {
    symbol: string | null;
}

const OptionGreeks: React.FC<OptionGreeksProps> = ({ symbol }) => {

    const [items, setItems] = useState<any[]>([]);

    // 使用 useQuery 自动管理数据获取，每当 symbol 变化时重新加载
    const { data: greeksData, error, isLoading } = useQuery(
        ['greeks', symbol],  // symbol 作为查询的 key，symbol 变化时会重新加载
        () => optionDataProvider.fetchOptionGreeks(symbol as string),
        {
            onSuccess(data) {
                const formattedItems = Object.keys(data.strike_prices).map((strikePrice) => {
                    const strikeData = data.strike_prices[strikePrice];
                    // console.log('Response data: ', strikeData);
                    return {
                        strikePrice, // 行权价格
                        callPosition: strikeData.call_option.position,
                        callDelta: strikeData.call_option.delta,
                        callGamma: strikeData.call_option.gamma,
                        callVega: strikeData.call_option.vega,
                        callTheta: strikeData.call_option.theta,
                        callVanna_sv: strikeData.call_option.vanna_sv,
                        callVanna_vs: strikeData.call_option.vanna_vs,
                        callDb: strikeData.call_option.db,
                        callDkurt: strikeData.call_option.dkurt,
                        callBid: strikeData.call_option.bid,
                        callAsk: strikeData.call_option.ask,
                        putDelta: strikeData.put_option.delta,
                        putPosition: strikeData.put_option.position,
                        putGamma: strikeData.put_option.gamma,
                        putVega: strikeData.put_option.vega,
                        putTheta: strikeData.put_option.theta,
                        putVanna_sv: strikeData.put_option.vanna_sv,
                        putVanna_vs: strikeData.put_option.vanna_vs,
                        putDb: strikeData.put_option.db,
                        putDkurt: strikeData.put_option.dkurt,
                        putBid: strikeData.put_option.bid,
                        putAsk: strikeData.put_option.ask,
                    };
                });

                setItems(formattedItems); // 更新表格项
            },
            refetchInterval: 3000, // 每隔 3 秒重新获取一次数据
            enabled: !!symbol,  // 只有当 symbol 存在时才启用查询
            refetchOnWindowFocus: false, // 禁用在窗口获得焦点时重新获取数据
        }
    );

    if (isLoading) {
        return <Text>Loading Greeks data...</Text>;
    }

    if (error) {
        return <Text>Error loading Greeks data</Text>;
    }

    if (!greeksData) {
        return <Text>No Greeks data available for {symbol}</Text>;
    }

    // 设置列
    const columns: IColumn[] = [
        { key: 'strikePrice', name: '行权价', fieldName: 'strikePrice', minWidth: 10, maxWidth: 50, isResizable: true },
        { key: 'callPosition', name: 'Call持仓', fieldName: 'callPosition', minWidth: 10, maxWidth: 60, isResizable: true },
        { key: 'putPosition', name: 'Put持仓', fieldName: 'putPosition', minWidth: 10, maxWidth: 60, isResizable: true },
        { key: 'callDelta', name: 'Delta.C', fieldName: 'callDelta', minWidth: 10, maxWidth: 50, isResizable: true },
        { key: 'putDelta', name: 'Delta.P', fieldName: 'putDelta', minWidth: 10, maxWidth: 50, isResizable: true },
        { key: 'vega', name: 'Vega', fieldName: 'callVega', minWidth: 10, maxWidth: 50, isResizable: true },
        { key: 'callTheta', name: 'Theta.C', fieldName: 'callTheta', minWidth: 10, maxWidth: 50, isResizable: true },
        { key: 'putTheta', name: 'Theta.P', fieldName: 'putTheta', minWidth: 10, maxWidth: 50, isResizable: true },
        { key: 'db', name: 'db', fieldName: 'callDb', minWidth: 10, maxWidth: 50, isResizable: true },
        { key: 'dkurt', name: 'dkurt', fieldName: 'callDkurt', minWidth: 10, maxWidth: 50, isResizable: true },
        { key: 'callbid', name: '买一价.C', fieldName: 'callBid', minWidth: 10, maxWidth: 60, isResizable: true },
        { key: 'callask', name: '卖一价.C', fieldName: 'callAsk', minWidth: 10, maxWidth: 60, isResizable: true },
        { key: 'putbid', name: '买一价.P', fieldName: 'putBid', minWidth: 10, maxWidth: 60, isResizable: true },
        { key: 'putask', name: '卖一价.P', fieldName: 'putAsk', minWidth: 10, maxWidth: 60, isResizable: true },
    ];

    const gridStyles: Partial<IDetailsListStyles> = {
        root: {
            overflowX: 'auto', // 禁止左右滚动
            overflowY: 'auto',
            height: '100%',
            width: '100%',
        },
        headerWrapper: {
            position: 'sticky', // 表头固定
            top: 0, // 距顶部的距离
            zIndex: 1, // 确保表头在内容上方
        },
    };

    return (
        <DetailsList
            items={items}
            columns={columns}
            selectionMode={SelectionMode.none}
            styles={gridStyles}
            compact={true}
        />
    );
};

export default OptionGreeks;