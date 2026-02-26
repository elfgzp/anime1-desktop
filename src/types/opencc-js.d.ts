declare module 'opencc-js' {
  export interface ConverterOptions {
    from: string
    to: string
  }

  export type Converter = (text: string) => string

  export function Converter(options: ConverterOptions): Converter
}
