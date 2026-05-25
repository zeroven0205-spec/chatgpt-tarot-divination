export type DivinationType =
  | 'tarot'
  | 'birthday'
  | 'new_name'
  | 'name'
  | 'dream'
  | 'plum_flower'
  | 'fate'

export interface NewNamePayload {
  surname: string
  sex: string
  birthday: string
  new_name_prompt: string
}

export interface PlumFlowerPayload {
  num1: number
  num2: number
}

export interface FatePayload {
  name1: string
  name2: string
}

export interface DivinationPayloadMap {
  tarot: {
    prompt: string
  }
  birthday: {
    prompt: string
    birthday: string
  }
  new_name: {
    prompt: string
    birthday: string
    new_name: NewNamePayload
  }
  name: {
    prompt: string
  }
  dream: {
    prompt: string
  }
  plum_flower: {
    prompt: string
    plum_flower: PlumFlowerPayload
  }
  fate: {
    prompt: string
    fate: FatePayload
  }
}

export type DivinationPayload<T extends DivinationType = DivinationType> =
  DivinationPayloadMap[T] & {
    prompt: string
  }

export type DivinationRequest<T extends DivinationType = DivinationType> =
  DivinationPayload<T> & {
    prompt_type: T
  }
